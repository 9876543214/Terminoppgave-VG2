Create database sosial_media;
create user 'sosial'@'%' identified by 'sosial123';
grant all privileges on 'sosial_media'.* to 'sosial'@'%';
exit;

-- logg inn med den nye brukeren

use sosial_media

CREATE TABLE users(
    user_id int not null AUTO_INCREMENT PRIMARY KEY,
    username varchar(255) not null,
    email varchar(255) not null,
    password_hash varchar(255) not null,
    salt varchar(255) not null,
    join_date varchar(255) not null
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

CREATE TABLE likes (
    user_id int not null,
    post_id bigint not null,
    CONSTRAINT fk_userlikes FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_postlikes FOREIGN KEY (post_id) REFERENCES posts(post_id)
);

CREATE TABLE comments (
    comment_id BIGINT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    post_id BIGINT NOT NULL,
    user_id INT NOT NULL,
    content TEXT,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_post_id FOREIGN KEY (post_id) REFERENCES posts(post_id)
);