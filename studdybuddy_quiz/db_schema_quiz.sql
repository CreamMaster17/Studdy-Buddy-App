-- Sprint 2 - Database Schema for Quiz History and Progress Tracking
-- Author: Samuel Gamon
-- 
-- This schema defines the database tables needed for:
--   - Saving quiz results and scores
--   - Tracking per-question responses
--   - Storing generated quiz snapshots
--   - Supporting the statistics dashboard and AI recommendations
--
-- Run this script against your PostgreSQL database to initialize the tables.

-- ============================================
-- Table: quiz_results
-- Stores the overall result of each quiz attempt
-- Linked to users via user_id (references the users table)
-- ============================================
CREATE TABLE IF NOT EXISTS quiz_results (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    quiz_title VARCHAR(255) NOT NULL,
    score_percentage DECIMAL(5,2) NOT NULL CHECK (score_percentage >= 0 AND score_percentage <= 100),
    correct_count INTEGER NOT NULL CHECK (correct_count >= 0),
    total_questions INTEGER NOT NULL CHECK (total_questions > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookup of a user's quiz history
CREATE INDEX IF NOT EXISTS idx_quiz_results_user_id 
    ON quiz_results(user_id);

-- Index for sorting by date (dashboard, recommendations)
CREATE INDEX IF NOT EXISTS idx_quiz_results_created_at 
    ON quiz_results(created_at DESC);

-- Composite index for user + date queries (stats, trends)
CREATE INDEX IF NOT EXISTS idx_quiz_results_user_date 
    ON quiz_results(user_id, created_at DESC);

-- ============================================
-- Table: quiz_question_results
-- Stores individual question responses within a quiz
-- Linked to quiz_results via foreign key
-- ============================================
CREATE TABLE IF NOT EXISTS quiz_question_results (
    id SERIAL PRIMARY KEY,
    quiz_result_id INTEGER NOT NULL REFERENCES quiz_results(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    user_answer VARCHAR(10) NOT NULL,
    correct_answer VARCHAR(10) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fetching question details by quiz result
CREATE INDEX IF NOT EXISTS idx_quiz_question_results_quiz_id 
    ON quiz_question_results(quiz_result_id);

-- ============================================
-- Table: generated_quizzes
-- Stores snapshots of AI-generated quizzes
-- Allows users to retake or review past generated quizzes
-- ============================================
CREATE TABLE IF NOT EXISTS generated_quizzes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    quiz_title VARCHAR(255) NOT NULL,
    quiz_data JSONB NOT NULL,
    source_notes_length INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for user's saved quizzes
CREATE INDEX IF NOT EXISTS idx_generated_quizzes_user_id 
    ON generated_quizzes(user_id);

-- ============================================
-- Sample test data (optional - for development/testing)
-- Uncomment and run if you need mock data for testing
-- ============================================
/*
-- Insert sample quiz results for user_id = 1
INSERT INTO quiz_results (user_id, quiz_title, score_percentage, correct_count, total_questions, created_at)
VALUES 
    (1, 'Biology - Cell Structure', 80.00, 4, 5, NOW() - INTERVAL '1 day'),
    (1, 'Biology - Cell Structure', 60.00, 3, 5, NOW() - INTERVAL '3 days'),
    (1, 'World History - WWII', 100.00, 5, 5, NOW() - INTERVAL '5 days'),
    (1, 'Chemistry - Periodic Table', 40.00, 2, 5, NOW() - INTERVAL '7 days'),
    (1, 'Chemistry - Periodic Table', 60.00, 3, 5, NOW() - INTERVAL '10 days');

-- Insert sample question results
INSERT INTO quiz_question_results (quiz_result_id, question_id, question_text, user_answer, correct_answer, is_correct, explanation)
VALUES 
    (1, 1, 'What is the powerhouse of the cell?', 'B', 'B', true, 'The mitochondria is known as the powerhouse of the cell.'),
    (1, 2, 'What does the nucleus contain?', 'A', 'A', true, 'The nucleus contains the cell genetic material (DNA).'),
    (1, 3, 'Which organelle is responsible for protein synthesis?', 'C', 'C', true, 'Ribosomes are responsible for protein synthesis.'),
    (1, 4, 'What is the function of the cell membrane?', 'D', 'D', true, 'The cell membrane controls what enters and exits the cell.'),
    (1, 5, 'Which structure is found in plant cells but not animal cells?', 'A', 'B', false, 'Cell walls are found in plant cells but not animal cells.');
*/
