begin;  
  
-- lift   
SET FOREIGN_KEY_CHECKS=0;  



alter table locations_locationtype add column slug varchar(50);
update locations_locationtype set slug=lower(name);
alter table locations_locationtype add unique(slug);

alter table locations_location add column parent_type_id integer;
update locations_location set parent_type_id = (select id from django_content_type where model = "location");
alter table locations_location add check (parent_id >= 0);

ALTER TABLE `locations_location` ADD CONSTRAINT `locations_location_parent_type_id_fkey` FOREIGN KEY (`parent_type_id`) REFERENCES `locations_location` (`parent_id`);

alter table locations_location drop constraint parent_id_refs_id_47ca058b;

CREATE TABLE locations_point (
    id serial NOT NULL PRIMARY KEY,
    latitude numeric(13, 10) NOT NULL,
    longitude numeric(13, 10) NOT NULL
);
alter table locations_location add column point_id integer ;

alter table locations_location add column type_slug varchar(50) ;

update locations_location set type_slug = (select slug from locations_locationtype t where t.id = type_id);

alter table locations_location drop column type_id;

alter table locations_locationtype drop constraint locations_locationtype_pkey;

alter table locations_locationtype drop column id;

alter table locations_locationtype alter column slug set not null;

alter table locations_locationtype add constraint locations_locationtype_pkey primary key(slug);

alter table locations_location rename column type_slug to type_id;


-- put back when you're done  
SET FOREIGN_KEY_CHECKS=1;  
  
commit;  
