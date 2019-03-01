CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS device;

CREATE TABLE device (
    uuid uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    value double precision,
    sent BOOLEAN default false,
    num_attempts SMALLINT default 0
);