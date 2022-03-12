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

SELECT create_hypertable('ticks','time', if_not_exists => TRUE);