# Django LMS (Learning Management System)

Welcome to the Django LMS project! This project aims to provide a comprehensive learning management system with features like user profiles, messaging, notifications, job listings, groups, followers, events, courses, connections, companies, and certifications.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Setup](#setup)
- [Models](#models)
  - [Profiles](#profiles)
  - [Notifications](#notifications)
  - [Messaging](#messaging)
  - [Blog](#blog)
  - [Jobs](#jobs)
  - [Groups](#groups)
  - [Followers](#followers)
  - [Events](#events)
  - [Courses](#courses)
  - [Connections](#connections)
  - [Companies](#companies)
  - [Certifications](#certifications)
- [Contributing](#contributing)
- [License](#license)

## Overview

Django LMS is a robust learning management system built using Django. It allows users to create profiles, follow other users, join groups, enroll in courses, apply for jobs, and much more. The system is designed to be scalable and flexible, catering to various educational and professional networking needs.

## Features

- User Profiles with skills, experiences, and endorsements
- Messaging and notifications
- Job listings and applications
- Group creation and management
- Follower system
- Event creation and attendance
- Course enrollment and completion
- Connection requests and recommendations
- Company profiles and updates
- Certification management

## Setup Instructions

To set up this project locally, follow these steps:

1. **Clone the repository:**

    ```bash
    git clone https://github.com/AbdullahBakir97/Django--LMS--Learning-Management-System.git
    cd Django--LMS--Learning-Management-System
    ```

2. **Create a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Apply migrations:**

    ```bash
    python manage.py migrate
    ```

5. **Create a superuser:**

    ```bash
    python manage.py createsuperuser
    ```

6. **Run the development server:**

    ```bash
    python manage.py runserver
    ```

7. **Access the application:**

    Open your web browser and go to [http://localhost:8000](http://localhost:8000)



# Models

## Profiles

**UserProfile**:

🧑‍💼 Stores user details and relations to skills, experiences, educations, endorsements, groups, connections, notifications, and certifications.

## Skill, Experience, Education, Endorsement:
📚 Auxiliary models to store user skills, work experience, educational background, and endorsements from other users.

## Notifications

**NotificationType, Notification, NotificationTemplate**:
🔔 Models to manage different types of notifications, notification instances, and templates for notification messages.

## Messaging

**Tag, Share, Reaction, ChatRoom, Message**:
💬 Models to handle tags, shares, reactions, chat rooms, and messages between users.

## Blog

**Post, Comment**:
💬 Models to handle posts, comments, tags, shares, reactions, and related interactions.

## Jobs

**JobListing, JobApplication, JobNotification**:
💼 Models for managing job listings, job applications, and notifications related to job activities.

## Groups

**Group, GroupMembership**:
👥 Models to manage user groups, group memberships, and group activities.

## Followers

**Follower, FollowRequest, FollowNotification**:
🔗 Models to manage followers, follow requests, and notifications related to following activities.

## Events

**Event**:
📅 Model to manage events organized by users, including event details and attendees.

## Courses

**Course, CourseEnrollment, CourseCompletion**:
🎓 Models to manage courses, course enrollments, and course completions, including certificates.

## Connections

**ConnectionRequest, Connection, Recommendation**:
🤝 Models to manage connection requests, established connections, and recommendations between users.

## Companies

**Company, CompanyUpdate**:
🏢 Models to manage company profiles, company members, followers, and updates.

## Certifications

**Certification**:
📜 Model to manage user certifications, related jobs, and related courses.



# Contributing
Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) for more information.

# License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
