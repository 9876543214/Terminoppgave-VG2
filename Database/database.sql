Create database sosial_media;
create user 'sosial'@'%' identified by 'sosial123';
grant all privileges on 'sosial_media'.* to 'sosial'@'%';
exit;

-- logg inn med den nye brukeren

use sosial_media

create table users(
    user_id int not null AUTO_INCREMENT PRIMARY KEY,
    username varchar(255) not null,
    email varchar(255) not null,
    password_hash varchar(255) not null
);



CREATE TABLE posts (
    post_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    content TEXT,
    media_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    visibility ENUM('public', 'private', 'friends_only') DEFAULT 'public',
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);