drop table if exists entries;
create table entries(
  id integer primary key autoincrement,
  mode text not null,
  temperature integer not null,
  fan text not null);

drop table if exists responses;
create table responses(
  id integer primary key autoincrement,
  response text not null);
