-- нициализация базы данных Minecraft Support Bot
CREATE DATABASE IF NOT EXISTS minecraft_support;
USE minecraft_support;

-- Создаем пользователя (на всякий случай)
CREATE USER IF NOT EXISTS 'minecraft_user'@'%' IDENTIFIED BY 'user_password';
GRANT ALL PRIVILEGES ON minecraft_support.* TO 'minecraft_user'@'%';
GRANT ALL PRIVILEGES ON minecraft_support.* TO 'minecraft_user'@'localhost';
FLUSH PRIVILEGES;

-- нформационное сообщение
SELECT '✅ аза данных Minecraft Support Bot готова к работе!' as status;
