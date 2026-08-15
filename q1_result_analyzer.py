"""
Q1: Student Result Analyzer
----------------------------
Stores a student's name and roll number, takes 5 subject marks,
calculates total and average, assigns a grade, and prints which
subjects the student scored below 40 in.
"""


def analyze_result(name, roll, marks):
    # Step 1: Calculate total and average
    total = sum(marks)
    average = total / len(marks)

    # Step 2: Assign grade based on average
    if average >= 90:
        grade = "A"
    elif average >= 75:
        grade = "B"
    elif average >= 60:
        grade = "C"
    elif average >= 40:
        grade = "D"
    else:
        grade = "Fail"

    # Step 3: Print student details
    print("Student: " + name + " (Roll: " + str(roll) + ")")
    print("Total: " + str(total) + ", Average: " + str(average))
    print("Grade: " + grade)

    # Step 4: Find subjects with marks below 40 using a loop
    failed_subjects = []
    for i in range(len(marks)):
        if marks[i] < 40:
            subject_number = i + 1
            failed_subjects.append("Subject " + str(subject_number))

    # Step 5: Print subjects below 40
    if len(failed_subjects) > 0:
        print("Subjects below 40: " + ", ".join(failed_subjects))
    else:
        print("Subjects below 40: None")


# Sample run
if __name__ == "__main__":
    name = "Aarav"
    roll = 101
    marks = [88.5, 35.0, 76.0, 92.5, 48.0]

    analyze_result(name, roll, marks)
