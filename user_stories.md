### **1. Generate Quiz Questions**

#### **Task 1.1: Generate Beginner-Level Questions**
- **User Story**: As a student, I want to receive beginner-level questions tailored to my selected programming language so that I can practice foundational concepts.
- **Steps**:
  1. Prompt the LLM to generate a beginner-level question for the selected programming language.
  2. Ensure the question is unique compared to previously generated ones.
  3. Display the question to the user.
- **Acceptance Criteria**:
  - The question must align with beginner-level difficulty.
  - The question must not repeat within the same session.
  - The question type should include MCQs, code-writing tasks, or theory-based questions.
- **Technical Notes**:
  - Use a hashing mechanism or database lookup to ensure uniqueness.
  - Store generated questions temporarily in the vector database for session tracking.
- **Prompt**: "Generate a unique beginner-level question for the programming language [insert language here]. Ensure the question is different from previously generated questions and includes a mix of MCQs, code-writing tasks, and theory-based questions."

#### **Task 1.2: Generate Medium-Level Questions**
- **User Story**: As a student, I want to receive medium-level questions tailored to my selected programming language so that I can practice intermediate concepts.
- **Steps**:
  1. Prompt the LLM to generate a medium-level question for the selected programming language.
  2. Ensure the question is unique compared to previously generated ones.
  3. Display the question to the user.
- **Acceptance Criteria**:
  - The question must align with medium-level difficulty.
  - The question must not repeat within the same session.
  - The question type should include practical coding challenges or problem-solving scenarios.
- **Technical Notes**:
  - Use a hashing mechanism or database lookup to ensure uniqueness.
  - Store generated questions temporarily in the vector database for session tracking.
- **Prompt**: "Generate a unique medium-level question for the programming language [insert language here]. The question should be different from previous ones and include practical coding challenges or problem-solving scenarios."

#### **Task 1.3: Generate Advanced-Level Questions**
- **User Story**: As a student, I want to receive advanced-level questions tailored to my selected programming language so that I can practice complex concepts.
- **Steps**:
  1. Prompt the LLM to generate an advanced-level question for the selected programming language.
  2. Ensure the question is unique compared to previously generated ones.
  3. Display the question to the user.
- **Acceptance Criteria**:
  - The question must align with advanced-level difficulty.
  - The question must not repeat within the same session.
  - The question type should test complex concepts, debugging skills, or optimization techniques.
- **Technical Notes**:
  - Use a hashing mechanism or database lookup to ensure uniqueness.
  - Store generated questions temporarily in the vector database for session tracking.
- **Prompt**: "Generate a unique advanced-level question for the programming language [insert language here]. The question should test complex concepts, debugging skills, or optimization techniques."

#### **Task 1.4: Handle Fallback Mechanism for LLM Failure**
- **User Story**: As a student, I want to receive a question even if the LLM fails so that my learning process is uninterrupted.
- **Steps**:
  1. Detect LLM API failure.
  2. Retrieve a pre-stored question from the database based on the selected programming language and difficulty level.
  3. Display the fallback question to the user.
- **Acceptance Criteria**:
  - A pre-stored question must be retrieved if the LLM fails.
  - The fallback question must match the selected programming language and difficulty level.
- **Technical Notes**:
  - Maintain a database of pre-written questions categorized by language and difficulty.
- **Prompt**: "If the LLM API fails, retrieve a pre-stored question from the database for the selected programming language and difficulty level."

---

### **2. Answer Submission & Code Execution**

#### **Task 2.1: Validate User Input Syntax**
- **User Story**: As a student, I want my submitted code to be validated for syntax errors so that I don’t waste time debugging invalid code.
- **Steps**:
  1. Check the submitted code for syntax errors.
  2. If errors are found, display an error message and prevent further execution.
- **Acceptance Criteria**:
  - Syntax errors must be detected before code execution.
  - Error messages must clearly indicate the issue.
- **Technical Notes**:
  - Use a syntax checker library specific to the programming language.
- **Prompt**: "Check the submitted code for syntax errors. If any errors are found, display an error message and do not proceed with execution."

#### **Task 2.2: Run Code Against Predefined Test Cases**
- **User Story**: As a student, I want my code to be tested against predefined test cases so that I know if my solution works correctly.
- **Steps**:
  1. Execute the submitted code against predefined test cases stored in the backend.
  2. Validate if the output matches the expected results for all test cases.
- **Acceptance Criteria**:
  - All test cases must pass for the answer to be marked correct.
  - Failed test cases must be logged for feedback.
- **Technical Notes**:
  - Use a sandboxed environment for secure code execution.
- **Prompt**: "Execute the submitted code against predefined test cases stored in the backend. Validate if the output matches the expected results for all test cases."

#### **Task 2.3: Provide Feedback for Correct/Incorrect Answers**
- **User Story**: As a student, I want to receive feedback on my answers so that I know how well I performed.
- **Steps**:
  1. If all test cases pass, display "Correct Answer ✅".
  2. Otherwise, show "Incorrect Answer ❌" along with details of failed test cases.
- **Acceptance Criteria**:
  - Feedback must clearly indicate whether the answer is correct or incorrect.
  - For incorrect answers, details of failed test cases must be provided.
- **Technical Notes**:
  - Log failed test cases in the database for analysis.
- **Prompt**: "If all test cases pass, display 'Correct Answer ✅'. Otherwise, show 'Incorrect Answer ❌' along with details of failed test cases."

#### **Task 2.4: Update User Progress**
- **User Story**: As a student, I want my quiz progress to be updated so that I can track my performance over time.
- **Steps**:
  1. Update the user's progress in the database, including the number of correct answers and total attempts.
- **Acceptance Criteria**:
  - Progress metrics must be updated accurately.
  - Metrics such as "8/10 correct" must be displayed.

- **Prompt**: "Update the user's progress in the database, including the number of correct answers and total attempts. For example, store '8/10 correct' for the current quiz."
p
#### **Task 2.5: Handle Exceptions (e.g., Infinite Loops)**
- **User Story**: As a student, I want the system to handle exceptions like infinite loops so that my code doesn’t crash the platform.
- **Steps**:
  1. Detect infinite loops during code execution.
  2. Terminate the process and display a warning message.
- **Acceptance Criteria**:
  - Infinite loops must be detected and terminated.
  - A warning message must be displayed to the user.
- **Technical Notes**:
  - Implement a timeout mechanism for code execution.
- **Prompt**: "If an infinite loop is detected during code execution, terminate the process and display a warning message to the user."

---

### **3. Generate Explanations for Questions**

#### **Task 3.1: Request Explanation for Correct Answers**
- **User Story**: As a student, I want to understand why my correct answer is right so that I can reinforce my knowledge.
- **Steps**:
  1. Request an explanation from the LLM for the correct answer.
  2. Display the explanation to the user.
- **Acceptance Criteria**:
  - The explanation must clarify why the correct answer is right.
- **Technical Notes**:
  - Use the LLM API to generate explanations dynamically.
- **Prompt**: "Generate an explanation for why the correct answer is right. Include key concepts and reasoning behind the solution."

#### **Task 3.2: Request Explanation for Incorrect Answers**
- **User Story**: As a student, I want to understand why my incorrect answer is wrong so that I can learn from my mistakes.
- **Steps**:
  1. Request an explanation from the LLM for the incorrect answer.
  2. Display the explanation to the user.
- **Acceptance Criteria**:
  - The explanation must highlight mistakes and suggest alternative approaches.
- **Technical Notes**:
  - Use the LLM API to generate explanations dynamically.
- **Prompt**: "Generate an explanation for why the submitted answer is incorrect. Highlight mistakes and suggest alternative approaches."

#### **Task 3.3: Handle Fallback Mechanism for LLM Failure**
- **User Story**: As a student, I want to receive an explanation even if the LLM fails so that my learning experience is uninterrupted.
- **Steps**:
  1. Detect LLM API failure.
  2. Retrieve a pre-written explanation from the database for the given question.
  3. Display the fallback explanation to the user.
- **Acceptance Criteria**:
  - A pre-written explanation must be retrieved if the LLM fails.
- **Technical Notes**:
  - Maintain a database of pre-written explanations.
- **Prompt**: "If the LLM fails to generate an explanation, retrieve a pre-written explanation from the database for the given question."

---

### **4. Leaderboard & User Progress Comparison**

#### **Task 4.1: Store User Performance Data**
- **User Story**: As a student, I want my performance data to be stored so that it can be used for ranking and comparison.
- **Steps**:
  1. Store the user’s quiz performance data in the database, including accuracy and speed.
- **Acceptance Criteria**:
  - Accuracy and speed metrics must be stored accurately.
- **Prompt**: "Store the user's quiz performance data in the database, including accuracy (percentage of correct answers) and speed (average time per question)."

#### **Task 4.2: Rank Users Based on Accuracy**
- **User Story**: As a student, I want to see rankings based on accuracy so that I can compare my performance with others.
- **Steps**:
  1. Retrieve all users’ performance data.
  2. Rank users based on accuracy.
  3. Display the top 10 users on the leaderboard.
- **Acceptance Criteria**:
  - Rankings must be based on accuracy.
  - Top 10 users must be displayed.
- **Technical Notes**:
  - Use database queries to rank users.
- **Prompt**: "Retrieve all users' performance data and rank them based on accuracy. Display the top 10 users on the leaderboard."

#### **Task 4.3: Rank Users Based on Speed**
- **User Story**: As a student, I want to see rankings based on speed so that I can compare my efficiency with others.
- **Steps**:
  1. Retrieve all users’ performance data.
  2. Rank users based on average time per question.
  3. Display the top 10 fastest users on the leaderboard.
- **Acceptance Criteria**:
  - Rankings must be based on speed.
  - Top 10 fastest users must be displayed.
- **Technical Notes**:
  - Use database queries to rank users.
- **Prompt**: "Retrieve all users' performance data and rank them based on average time per question. Display the top 10 fastest users on the leaderboard."

#### **Task 4.4: Compare User Performance with Friends/Global Users**
- **User Story**: As a student, I want to compare my performance with friends or global users so that I can gauge my standing.
- **Steps**:
  1. Allow users to compare their performance with specific friends or global users.
  2. Display comparative metrics such as accuracy and speed.
- **Acceptance Criteria**:
  - Comparative metrics must be displayed accurately.
- **Technical Notes**:
  - Use database queries to filter and compare data.
- **Prompt**: "Allow users to compare their performance with specific friends or global users. Display comparative metrics such as accuracy and speed."

#### **Task 4.5: Handle Unavailable Data**
- **User Story**: As a student, I want to be informed if leaderboard data is unavailable so that I know the status of the system.
- **Steps**:
  1. Detect unavailability of leaderboard data.
  2. Display a message indicating the unavailability.
- **Acceptance Criteria**:
  - A clear message must be displayed if data is unavailable.
- **Technical Notes**:
  - Use error handling to detect data unavailability.
- **Prompt**: "If leaderboard data is unavailable, display the message: 'Leaderboard data not available at the moment.'"

---

### **5. Compare Progress of Quizzes and Assignments**

#### **Task 5.1: Track Quiz Progress**
- **User Story**: As a student, I want my quiz progress to be tracked so that I can monitor my improvement over time.
- **Steps**:
  1. Store the user’s progress for each quiz attempt, including the number of correct answers, total questions, and time taken.
- **Acceptance Criteria**:
  - Quiz progress must be tracked accurately.
- **Technical Notes**:
  - Use the vector database to store quiz progress.
- **Prompt**: "Store the user's progress for each quiz attempt, including the number of correct answers, total questions, and time taken."

#### **Task 5.2: Track Assignment Progress**
- **User Story**: As a student, I want my assignment progress to be tracked so that I can monitor my improvement over time.
- **Steps**:
  1. Store the user’s progress for each assignment, including completion status, score, and feedback.
- **Acceptance Criteria**:
  - Assignment progress must be tracked accurately.
- **Technical Notes**:
  - Use the vector database to store assignment progress.
- **Prompt**: "Store the user's progress for each assignment, including completion status, score, and feedback."

#### **Task 5.3: Compare Quiz and Assignment Progress**
- **User Story**: As a student, I want to compare my quiz and assignment progress so that I can identify areas for improvement.
- **Steps**:
  1. Compare the user’s progress across quizzes and assignments.
  2. Display metrics such as improvement over time and areas needing improvement.
- **Acceptance Criteria**:
  - Comparative metrics must be displayed accurately.
- **Technical Notes**:
  - Use database queries to analyze progress data.
- **Prompt**: "Compare the user's progress across quizzes and assignments. Display metrics such as improvement over time and areas needing improvement."