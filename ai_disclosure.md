# AI Use Disclosure

I used an AI assistants Claude and Deepseek during this project. Here's exactly
how and where:

**What AI helped with:**
- Reviewing each file for bugs and erro handling
- Suggesting structural improvements, like keeping validation in
  services.py instead of models.py
- Spotting edge cases, like catching sqlite3.IntegrityError when a
  duplicate email is inserted
- Reviewing the wording of documentation

**What AI did NOT do:**
- Design the problem or choose features
- Design all classes i used
- Design all error handling used 
- Model classes attributes and methonds
- Write the final code 
- Decide the database schema


**Verification:**
Every file was read line by line, run against the test suite, and
exercised through the menu before submission. 