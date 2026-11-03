"""Opt-in demo content for the Community feed (SEED_DEMO_COMMUNITY=1).

Mirrors the sample questions the frontend used before Community moved to the backend.
Authors are display labels only, never accounts, and their seeded vote counts are shown
as a starting score, so no fake users are created.
"""

DEMO_POSTS = [{'title': 'What exactly counts towards the 75% attendance rule?',
  'body': 'Does attendance in labs count separately from theory classes, or is it all pooled into one '
          'percentage per course?',
  'tags': ['Academics', 'Attendance'],
  'author': 'Kavya R.',
  'days_ago': 2,
  'votes': 14,
  'answers': [{'author': 'Sanya Mehta',
               'body': 'Labs and theory are tracked separately per course code — check the per-course '
                       'breakup on the portal, not just the overall number.',
               'days_ago': 2,
               'votes': 19,
               'replies': [{'author': 'Kavya R.',
                            'body': 'That explains it, thank you!',
                            'days_ago': 1,
                            'votes': 2,
                            'replies': []}]},
              {'author': 'Rahul Menon',
               'body': 'Also worth noting condonation forms exist if you drop just below 75% for medical '
                       'reasons.',
               'days_ago': 1,
               'votes': 6,
               'replies': []}]},
 {'title': 'Best way to prepare for the OS end-sem besides PYQs?',
  'body': 'Finished the previous year questions twice already, looking for anything else that actually '
          'helped people.',
  'tags': ['Academics', 'Exams'],
  'author': 'Devansh P.',
  'days_ago': 4,
  'votes': 22,
  'answers': [{'author': 'Diya Shetty',
               'body': 'Gate Smashers playlist on OS plus re-deriving the scheduling numericals by hand '
                       'helped me more than re-reading notes.',
               'days_ago': 3,
               'votes': 15,
               'replies': []},
              {'author': 'Varun Kapoor',
               'body': 'Form a study group and explain deadlock avoidance to each other out loud, it exposes '
                       'gaps fast.',
               'days_ago': 3,
               'votes': 11,
               'replies': [{'author': 'Devansh P.',
                            'body': 'Doing this tonight, thanks!',
                            'days_ago': 2,
                            'votes': 1,
                            'replies': []}]},
              {'author': 'Kavya R.',
               'body': "Professor Saldanha's office hours on Thursdays are criminally underused, go ask "
                       'there.',
               'days_ago': 2,
               'votes': 4,
               'replies': []}]},
 {'title': 'Anyone know how hostel outpass approval timing actually works?',
  'body': 'Submitted an outpass request two days ago and it still shows pending. Is there a usual turnaround '
          'time?',
  'tags': ['Hostel', 'Campus Life'],
  'author': 'Ishaan T.',
  'days_ago': 0.25,
  'votes': 3,
  'answers': []},
 {'title': 'Is it worth joining both IEEE and Robotics Club or should I pick one?',
  'body': "Both are doing interesting projects this semester and I can't decide, curious what people who've "
          'done both think.',
  'tags': ['Clubs'],
  'author': 'Meera Joshi',
  'days_ago': 1,
  'votes': 9,
  'answers': [{'author': 'Sanya Mehta',
               'body': 'Depends on your semester load — I did both in 3rd sem and it was tight but doable if '
                       "the projects don't overlap in deadlines.",
               'days_ago': 0.83,
               'votes': 8,
               'replies': []}]},
 {'title': 'Elective registration closed before I could pick — now what?',
  'body': 'Missed the window for elective registration by a day. Is there a late-add process or do I just '
          'get auto-assigned?',
  'tags': ['Academics', 'Registration'],
  'author': 'Rhea D souza',
  'days_ago': 3,
  'votes': 7,
  'answers': []},
 {'title': 'How do people usually fund side projects / hackathon travel?',
  'body': "Our team qualified for an offline hackathon round and travel + stay isn't cheap. Does the college "
          'sponsor anything for this?',
  'tags': ['Opportunities', 'Clubs'],
  'author': 'Aarav Singh',
  'days_ago': 5,
  'votes': 18,
  'answers': [{'author': 'Diya Shetty',
               'body': 'Student Innovation Cell has a travel grant form, worth 60–70% reimbursement if you '
                       'place or even just qualify for finals.',
               'days_ago': 4,
               'votes': 21,
               'replies': [{'author': 'Aarav Singh',
                            'body': "This is huge, didn't know this existed.",
                            'days_ago': 4,
                            'votes': 3,
                            'replies': []}]},
              {'author': 'Rahul Menon',
               'body': "Your department also sometimes has a small discretionary fund, ask your HOD's office "
                       'directly.',
               'days_ago': 3,
               'votes': 5,
               'replies': []}]}]
