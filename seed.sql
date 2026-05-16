-- Clean out any existing data to prevent primary key conflicts during tests
TRUNCATE TABLE automation_errors, job_postings, companies RESTART IDENTITY CASCADE;

-- 1. Inject Test Target Employers
INSERT INTO companies (company_name, career_page_url) VALUES
('Charleston Tech Logistics', 'https://example.com'),
('Palmetto Cloud Systems', 'https://example.com'),
('Lowcountry Automated Analytics', 'https://example.com');

-- 2. Inject Mixed Test Job Profiles (Targeting Charleston, Remote)
INSERT INTO job_postings (company_id, job_title, job_url, job_description, status) VALUES
(1, 'Senior Data Engineer (Remote)', 'https://linkedin.com', 'Looking for a Senior Python and SQL expert to optimize PostgreSQL storage clusters.', 'Scraped'),
(1, 'Director of Analytics Architecture', 'https://linkedin.com', 'Strategic leadership post scaling organizational databases.', 'Scraped'), -- Should trigger TITLE_BLACKLIST
(2, 'Python Backend Engineer (100% Remote)', 'https://linkedin.com', 'Write core automation frameworks, build RESTful APIs with FastAPI and implement HTML frontends.', 'Scraped'),
(3, 'Database Administrator (PostgreSQL)', 'https://linkedin.com', 'Maintain physical data safety limits, check error indices, write structured storage migrations.', 'Scraped'),
(3, 'Principal Integration Engineer', 'https://linkedin.com', 'High-level architectural oversight across multi-cloud integrations.', 'Scraped'); -- Should trigger TITLE_BLACKLIST
