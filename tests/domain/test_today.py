from datetime import timedelta

from recto.domain.today import NEW_PER_DAY, plan_today
from tests.object_mothers.knowledge import NOW, KnowledgeMother


def test_due_knowledge_comes_most_overdue_first() -> None:
    yesterday = KnowledgeMother.new().with_id("yesterday").due_at(NOW - timedelta(days=1)).build()
    last_week = KnowledgeMother.new().with_id("last-week").due_at(NOW - timedelta(days=7)).build()

    today = plan_today([yesterday, last_week], NOW)

    assert [item.id for item in today.due] == ["last-week", "yesterday"]


def test_knowledge_due_later_is_not_asked() -> None:
    tomorrow = KnowledgeMother.new().due_at(NOW + timedelta(days=1)).build()

    assert plan_today([tomorrow], NOW).queue == ()


def test_knowledge_due_within_minutes_is_asked_last() -> None:
    soon = KnowledgeMother.new().with_id("soon").due_at(NOW + timedelta(minutes=5)).build()
    new = KnowledgeMother.new().with_id("new").build()

    today = plan_today([soon, new], NOW)

    assert [item.id for item in today.queue] == ["new", "soon"]
    assert today.to_review == 1


def test_new_knowledge_comes_in_file_order_up_to_the_daily_limit() -> None:
    new = [KnowledgeMother.new().with_id(f"k{n}").at_position(n).build() for n in reversed(range(15))]

    today = plan_today(new, NOW)

    assert [item.id for item in today.new] == [f"k{n}" for n in range(NEW_PER_DAY)]


def test_knowledge_introduced_today_counts_toward_the_daily_limit() -> None:
    introduced = [
        KnowledgeMother.new()
        .with_id(f"seen{n}")
        .introduced_at(NOW - timedelta(hours=1))
        .due_at(NOW + timedelta(days=1))
        .build()
        for n in range(4)
    ]
    new = [KnowledgeMother.new().with_id(f"k{n}").at_position(n).build() for n in range(15)]

    assert len(plan_today([*introduced, *new], NOW).new) == NEW_PER_DAY - 4


def test_knowledge_introduced_yesterday_does_not_count() -> None:
    introduced = KnowledgeMother.new().introduced_at(NOW - timedelta(days=1)).due_at(NOW + timedelta(days=1)).build()
    new = [KnowledgeMother.new().with_id(f"k{n}").at_position(n).build() for n in range(15)]

    assert len(plan_today([introduced, *new], NOW).new) == NEW_PER_DAY
