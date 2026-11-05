PRAGMA foreign_keys = ON;

CREATE TABLE dataset_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE topics (
    id     INTEGER PRIMARY KEY,
    slug   TEXT NOT NULL UNIQUE,
    label  TEXT NOT NULL,
    domain TEXT NOT NULL
);

CREATE TABLE users (
    id                   INTEGER PRIMARY KEY,
    first_name           TEXT NOT NULL,
    last_name            TEXT NOT NULL,
    has_photo            INTEGER NOT NULL CHECK (has_photo IN (0, 1)),
    bio                  TEXT,
    job_title            TEXT,
    company              TEXT,
    industry             TEXT,
    location             TEXT,
    joined_at            TEXT NOT NULL,
    profile_completeness REAL NOT NULL CHECK (profile_completeness BETWEEN 0 AND 1)
);

CREATE TABLE user_topic_interests (
    user_id  INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES topics (id),
    PRIMARY KEY (user_id, topic_id)
) WITHOUT ROWID;

CREATE TABLE circles (
    id                INTEGER PRIMARY KEY,
    name              TEXT NOT NULL,
    slug              TEXT NOT NULL UNIQUE,
    description       TEXT,
    cover_image_url   TEXT,
    format            TEXT NOT NULL CHECK (format IN ('in_person', 'virtual', 'hybrid')),
    access            TEXT NOT NULL CHECK (access IN ('public', 'unlisted')),
    join_policy       TEXT NOT NULL CHECK (join_policy IN ('open', 'request')),
    max_members       INTEGER CHECK (max_members IS NULL OR max_members > 0),
    member_count      INTEGER NOT NULL CHECK (member_count >= 0),
    created_at        TEXT NOT NULL,
    last_activity_at  TEXT NOT NULL,
    feed_posts_30d    INTEGER NOT NULL CHECK (feed_posts_30d >= 0),
    chat_messages_30d INTEGER NOT NULL CHECK (chat_messages_30d >= 0)
);

CREATE TABLE circle_topics (
    circle_id INTEGER NOT NULL UNIQUE REFERENCES circles (id) ON DELETE CASCADE,
    topic_id  INTEGER NOT NULL REFERENCES topics (id),
    PRIMARY KEY (circle_id, topic_id)
) WITHOUT ROWID;

CREATE TABLE circle_tags (
    circle_id INTEGER NOT NULL REFERENCES circles (id) ON DELETE CASCADE,
    tag       TEXT NOT NULL CHECK (length(tag) > 0),
    PRIMARY KEY (circle_id, tag)
) WITHOUT ROWID;

CREATE TABLE circle_memberships (
    id        INTEGER PRIMARY KEY,
    circle_id INTEGER NOT NULL REFERENCES circles (id) ON DELETE CASCADE,
    user_id   INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    role      TEXT NOT NULL CHECK (role IN ('member', 'leader')),
    joined_at TEXT NOT NULL
);

CREATE TABLE circle_activity (
    id             INTEGER PRIMARY KEY,
    circle_id      INTEGER NOT NULL REFERENCES circles (id) ON DELETE CASCADE,
    author_user_id INTEGER NOT NULL REFERENCES users (id),
    body           TEXT NOT NULL,
    reaction_count INTEGER NOT NULL CHECK (reaction_count >= 0),
    comment_count  INTEGER NOT NULL CHECK (comment_count >= 0),
    save_count     INTEGER NOT NULL CHECK (save_count >= 0),
    created_at     TEXT NOT NULL
);

CREATE TABLE circle_features (
    circle_id                INTEGER PRIMARY KEY REFERENCES circles (id) ON DELETE CASCADE,
    activity_score           REAL NOT NULL CHECK (activity_score BETWEEN 0 AND 1),
    engagement_per_post_30d  REAL NOT NULL CHECK (engagement_per_post_30d >= 0),
    days_since_last_activity REAL NOT NULL CHECK (days_since_last_activity >= 0),
    seats_left               INTEGER CHECK (seats_left IS NULL OR seats_left >= 0),
    is_full                  INTEGER NOT NULL CHECK (is_full IN (0, 1)),
    is_active                INTEGER NOT NULL CHECK (is_active IN (0, 1)),
    dedupe_cluster_id        INTEGER NOT NULL REFERENCES circles (id),
    location_key             TEXT,
    location_label           TEXT,
    CHECK ((location_key IS NULL) = (location_label IS NULL))
);

CREATE INDEX idx_circle_memberships_user ON circle_memberships (user_id);
CREATE UNIQUE INDEX idx_circle_memberships_circle_user ON circle_memberships (circle_id, user_id);
CREATE INDEX idx_circle_topics_topic_circle ON circle_topics (topic_id, circle_id);
CREATE INDEX idx_circle_features_active_full ON circle_features (is_active, is_full);
