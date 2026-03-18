# LMS Agent - Test Prompts for All Tools

This document contains test prompts for every tool across all sub-agents to verify each functionality is working properly.

---

## Architecture Overview

```
LMS_Executive (root orchestrator)
├── PDF_Handler            — upload, list documents
├── Quiz_Master            — generate quizzes, record answers, retry
├── Quiz_Historian         — history, session details, document stats
├── LearningContent_Agent  — Q&A, summaries, flashcards
├── AI_Tutor               — Socratic tutoring, examples, notes
├── Community_Agent        — publish content
```

**Note:** Document deletion is not supported. If asked to delete a document, the agent will politely inform you that this feature is unavailable.

---

## PDF_Handler Agent Tools

### 1. `upload_pdf`
**Test Prompt:**
```
Upload a PDF file named "Python_Basics.pdf" for me
```
*Note: You can also drag and drop a PDF file in the ADK Web chat.*

---

### 2. `batch_upload_pdf`
**Test Prompt:**
```
Upload these PDFs: file1.pdf, file2.pdf, file3.pdf
```
*Note: You can also drag and drop multiple PDF files at once in the ADK Web chat.*

**Alternative:**
```
I want to upload my entire semester's materials - here are 5 PDFs
```

---

### 3. `list_files`
**Test Prompt:**
```
Show me all my uploaded PDF files
```

---

## Quiz_Master Agent Tools

### 4. `generate_quiz`
**Test Prompt:**
```
Generate a 5 question quiz from my uploaded Python document
```

---

### 5. `record_answer`
**Test Prompt:**
```
My answer is option B
```
*Note: Used during an active quiz session. First generate a quiz, then use this to answer questions.*

---

### 6. `complete_quiz`
**Test Prompt:**
```
I want to finish the quiz now and see my results
```
*Note: Use this during an active quiz to end it and see the final score.*

---

### 7. `retry_quiz`
**Test Prompt:**
```
I want to retry the questions I got wrong in my last quiz
```

---

## Quiz_Historian Agent Tools

### 8. `quiz_history`
**Test Prompt:**
```
Show me my quiz history and all my past scores
```

**Filter by document:**
```
Show me my quiz history for the Python_Basics document
```

---

### 9. `session_details`
**Test Prompt:**
```
Show me the details of my last quiz session
```

**With a specific session ID:**
```
Show me the full breakdown for quiz session abc123
```

---

### 10. `document_stats`
**Test Prompt:**
```
What are my performance stats for the Python document?
```

**All documents:**
```
Give me an overview of my performance across all documents
```

---

## LearningContent_Agent Tools

### 11. `ask_question`
**Test Prompt:**
```
What are the main topics covered in Python_Basics.pdf?
```

**Alternative:**
```
Explain what a Python decorator is based on my uploaded document
```

---

### 12. `generate_summary`
**Test Prompt (brief):**
```
Give me a brief summary of Python_Basics.pdf
```

**Detailed summary:**
```
Generate a detailed summary of my Python document
```

**Key points:**
```
What are the key points from Python_Basics.pdf?
```

---

### 13. `generate_flashcards`
**Test Prompt:**
```
Generate 10 flashcards from Python_Basics.pdf
```

**With topic focus:**
```
Create 15 flashcards about functions from my Python document
```

---

## AI_Tutor Agent Tools

### 14. `start_tutoring_session`
**Test Prompt:**
```
Tutor me on Python functions from Python_Basics.pdf
```

**With difficulty level:**
```
Start a beginner-level tutoring session on loops using my Python document
```

---

### 15. `ask_followup`
**Test Prompt:**
```
I think a function is a block of reusable code, is that right?
```
*Note: Used during an active tutoring session to continue the dialogue.*

---

### 16. `check_understanding`
**Test Prompt:**
```
Check if I understand what we just covered
```

**On a specific concept:**
```
Quiz me on Python decorators to see if I understood
```

---

### 17. `save_learning_notes`
**Test Prompt:**
```
Save this note: A lambda function is a small anonymous function that can have any number of arguments but only one expression
```

**Alternative:**
```
Note this down: generators use yield instead of return and are memory efficient
```

---

### 18. `get_learning_notes`
**Test Prompt:**
```
Show me all my saved learning notes
```

**Filter by topic:**
```
Show my notes on Python functions
```

**Filter by document:**
```
Get my notes for Python_Basics.pdf
```

---

## Community_Agent Tools

### 19. `publish_to_community`
**Test Prompt:**
```
Publish my recently generated quiz to the community
```

**Alternative:**
```
Share my flashcards with other students
```

**Another:**
```
Upload my latest quiz to the community hub so others can practice
```

---

## Complete End-to-End Testing Workflow

1. **Upload a document:**
   ```
   Upload test.pdf
   ```

2. **Verify upload:**
   ```
   List my files
   ```

3. **Ask about content:**
   ```
   What is this document about?
   ```

4. **Get a summary:**
   ```
   Give me a brief summary of test.pdf
   ```

5. **Generate flashcards:**
   ```
   Create 10 flashcards from test.pdf
   ```

6. **Take a quiz:**
   ```
   Quiz me on this document with 5 questions
   ```

7. **Answer questions:**
   ```
   My answer is A
   ```
   *(Repeat for each question)*

8. **Complete quiz:**
   ```
   Finish quiz
   ```

9. **Check history:**
   ```
   Show my quiz history
   ```

10. **View session details:**
    ```
    Show details of my last quiz
    ```

11. **Check document stats:**
    ```
    Show my stats for test.pdf
    ```

12. **Retry wrong answers:**
    ```
    Retry my mistakes
    ```

13. **Start a tutoring session:**
    ```
    Tutor me on the main topic from test.pdf
    ```

14. **Ask a follow-up:**
    ```
    Can you explain that concept differently?
    ```

15. **Check understanding:**
    ```
    Check if I understood what we covered
    ```

16. **Save a note:**
    ```
    Save this note: <your key insight here>
    ```

17. **Retrieve notes:**
    ```
    Show my saved learning notes
    ```

18. **Publish to community:**
    ```
    Publish my recently generated quiz to the community
    ```

---

## Quick Reference (One-Liners)

| Tool | Agent | Quick Test Prompt |
|------|-------|-------------------|
| `upload_pdf` | PDF_Handler | `Upload sample.pdf` |
| `batch_upload_pdf` | PDF_Handler | `Upload file1.pdf, file2.pdf, file3.pdf` |
| `list_files` | PDF_Handler | `List files` |
| `generate_quiz` | Quiz_Master | `Quiz me with 5 questions on sample.pdf` |
| `record_answer` | Quiz_Master | `Answer: C` |
| `complete_quiz` | Quiz_Master | `End quiz` |
| `retry_quiz` | Quiz_Master | `Retry wrong answers` |
| `quiz_history` | Quiz_Historian | `Show history` |
| `session_details` | Quiz_Historian | `Show last session` |
| `document_stats` | Quiz_Historian | `Show document stats` |
| `ask_question` | LearningContent_Agent | `What are the key points in sample.pdf?` |
| `generate_summary` | LearningContent_Agent | `Summarize sample.pdf` |
| `generate_flashcards` | LearningContent_Agent | `Make 10 flashcards from sample.pdf` |
| `start_tutoring_session` | AI_Tutor | `Tutor me on the main topic of sample.pdf` |
| `ask_followup` | AI_Tutor | `I think I understand - can you confirm?` |
| `check_understanding` | AI_Tutor | `Check if I understood` |
| `save_learning_notes` | AI_Tutor | `Save note: <insight>` |
| `get_learning_notes` | AI_Tutor | `Show my learning notes` |
| `publish_to_community` | Community_Agent | `Publish my quiz to the community` |


---

## Testing Tips

1. **Agent Routing:** The LMS_Executive automatically routes to the correct sub-agent based on intent.
2. **PDF Required:** Most features require at least one PDF to be uploaded first.
3. **Quiz Context:** `record_answer` and `complete_quiz` only work during an active quiz session.
4. **Tutoring Context:** `ask_followup` and `check_understanding` work best during an active tutoring session.
5. **User Context:** All tools maintain per-user data using session context — no cross-user data leakage.
6. **Document Names:** Fuzzy matching is supported — you don't need to type the exact filename (e.g., "Python" matches "Python_Basics.pdf").

---

## Expected Behaviors

| Scenario | Expected Response |
|----------|-------------------|
| No PDFs uploaded | `ask_question`, `generate_quiz`, `start_tutoring_session` will prompt you to upload a PDF first |
| No active quiz | `record_answer`, `complete_quiz` will notify you to start a quiz first |
| No active tutoring session | `ask_followup`, `check_understanding` will prompt you to start a session first |
| No quiz history | `quiz_history`, `session_details`, `document_stats` return empty results for new users |
| Asked to delete a document | Agent informs you that document deletion is not supported |
| Invalid summary type | `generate_summary` accepts only `"brief"`, `"detailed"`, or `"key_points"` |
| Flashcard limit exceeded | `generate_flashcards` caps at 50 flashcards |
| No recent content to publish | `publish_to_community` will inform you to generate a quiz or flashcards first |

---

*Updated: 2026-02-26*
