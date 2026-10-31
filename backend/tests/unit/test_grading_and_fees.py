from app.api.v1.examinations import calculate_grade


def test_calculate_grade_standards():
    # 81 - 100 -> A
    grade_100, _ = calculate_grade(100.0, 100.0)
    assert grade_100 == "A"

    grade_85, _ = calculate_grade(85.0, 100.0)
    assert grade_85 == "A"

    # 61 - 80 -> B
    grade_75, _ = calculate_grade(75.0, 100.0)
    assert grade_75 == "B"

    # 41 - 60 -> C
    grade_55, _ = calculate_grade(55.0, 100.0)
    assert grade_55 == "C"

    # 21 - 40 -> D
    grade_30, _ = calculate_grade(30.0, 100.0)
    assert grade_30 == "D"

    # 0 - 20 -> F
    grade_15, _ = calculate_grade(15.0, 100.0)
    assert grade_15 == "F"


def test_calculate_grade_different_max_score():
    # Test on a paper out of 50 marks: 45/50 is 90% -> A
    grade, _ = calculate_grade(45.0, 50.0)
    assert grade == "A"

    # 25/50 is 50% -> C
    grade_c, _ = calculate_grade(25.0, 50.0)
    assert grade_c == "C"
