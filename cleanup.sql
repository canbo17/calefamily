BEGIN TRANSACTION;

-- 1) Remove all “New registration request” messages
DELETE FROM messages
 WHERE sender_id = 0
   AND content LIKE 'New registration request:%';

-- 2) Also remove any stray “New registration:” messages
DELETE FROM messages
 WHERE sender_id = 0
   AND content LIKE 'New registration:%';

-- 3) Delete the two test users entirely
DELETE FROM users
 WHERE username IN ('test01','test','necati');

COMMIT;

