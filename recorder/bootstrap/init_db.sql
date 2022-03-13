CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

CREATE TABLE IF NOT EXISTS "public".ticks ( time TIMESTAMPTZ,
	exchange varchar NOT NULL ,
	pair varchar NOT NULL ,
	opening_price double PRECISION NULL ,
	highest_price double PRECISION NULL ,
	lowest_price double PRECISION NULL ,
	closing_price double PRECISION NULL ,
	volume_base double PRECISION NULL ,
	volume_coin double PRECISION NULL
);

CREATE TABLE IF NOT EXISTS "public".indicators ( time TIMESTAMPTZ,
    exchange varchar NOT NULL,
    pair varchar NOT NULL,
    name varchar NOT NULL,
    value1 double PRECISION NOT NULL,
    value2 double PRECISION NULL,
    value3 double PRECISION NULL,
    value4 double PRECISION NULL
);

SELECT create_hypertable('ticks','time', if_not_exists => TRUE);
SELECT create_hypertable('indicators','time', if_not_exists => TRUE);