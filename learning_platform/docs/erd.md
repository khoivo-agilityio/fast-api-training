// Use DBML to define your database structure
// Docs: https://dbml.dbdiagram.io/docs

Table User {
  id uuid [pk]
  email varchar [unique]
  role varchar // admin, instructor, student
  password varchar
  display_name varchar [default: '']
  avatar varchar
  created_at datetime [default: `now()`]
}

Table Course {
  id uuid [pk]
  instructor uuid [ref: > User.id]
  title varchar [unique]
  description varchar
  created_at datetime [default: `now()`]
  updated_at datetime [default: `now()`]
}

Table Lesson {
  id uuid [pk]
  course uuid [ref: > Course.id]
  title varchar
  timeline varchar
  content text
  order int
  created_at datetime [default: `now()`]
  updated_at datetime [default: `now()`]
}

Table Progress {
  id uuid [pk]
  user uuid [ref: > User.id]
  lesson uuid [ref: > Lesson.id]
  status varchar // not_started, in_progress, completed
  accessed_at datetime [default: `now()`]
  completed_at datetime
}

Table Enrollment {
  id uuid [pk]
  user uuid [ref: > User.id]
  course uuid [ref: > Course.id]
  created_at datetime [default: `now()`]
}

Table Quiz {
  id uuid [pk]
  lesson uuid [ref: > Lesson.id]
  title varchar
  description varchar
  time_limit interval
}

Table Question {
  id uuid [pk]
  quiz uuid [ref: > Quiz.id]
  text text
  type varchar // mcq, text
  options json
  correct_answer varchar
}

Table Submission {
  id uuid [pk]
  user uuid [ref: > User.id]
  quiz uuid [ref: > Quiz.id]
  score float
  submitted_at datetime [default: `now()`]
}

Table Answer {
  id uuid [pk]
  submission uuid [ref: > Submission.id]
  question uuid [ref: > Question.id]
  text text
  is_correct boolean
}
