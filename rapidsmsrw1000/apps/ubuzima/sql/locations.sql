ALTER TABLE `locations_locationtype` ADD UNIQUE (
`name`
);
INSERT INTO `ubuzima`.`locations_locationtype` (
`id` ,
`name`
)
VALUES (
NULL , 'Cell'
);
ALTER TABLE `locations_location` ADD `cell_id` INT NULL AFTER `parent_id`;
ALTER TABLE `locations_location` ADD `sector_id` INT NULL AFTER `cell_id`;
ALTER TABLE `locations_location` ADD `district_id` INT NULL AFTER `sector_id`;
ALTER TABLE `locations_location` ADD `province_id` INT NULL AFTER `district_id`;
ALTER TABLE `locations_location` ADD `nation_id` INT NULL AFTER `province_id`;
ALTER TABLE `locations_location` ADD `population` INT NULL AFTER `nation_id`;
ALTER TABLE `locations_location` ADD `women` INT NULL AFTER `population`;

ALTER TABLE `locations_location` ADD CONSTRAINT `type_id_refs_id_6eefe411` FOREIGN KEY (`type_id`) REFERENCES `locations_locationtype` (`id`);
ALTER TABLE `locations_location` ADD CONSTRAINT `parent_id_refs_id_47ca058b` FOREIGN KEY (`parent_id`) REFERENCES `locations_location` (`id`);
ALTER TABLE `locations_location` ADD CONSTRAINT `cell_id_refs_id_47ca058b` FOREIGN KEY (`cell_id`) REFERENCES `locations_location` (`id`);
ALTER TABLE `locations_location` ADD CONSTRAINT `sector_id_refs_id_47ca058b` FOREIGN KEY (`sector_id`) REFERENCES `locations_location` (`id`);
ALTER TABLE `locations_location` ADD CONSTRAINT `district_id_refs_id_47ca058b` FOREIGN KEY (`district_id`) REFERENCES `locations_location` (`id`);
ALTER TABLE `locations_location` ADD CONSTRAINT `province_id_refs_id_47ca058b` FOREIGN KEY (`province_id`) REFERENCES `locations_location` (`id`);
ALTER TABLE `locations_location` ADD CONSTRAINT `nation_id_refs_id_47ca058b` FOREIGN KEY (`nation_id`) REFERENCES `locations_location` (`id`);

COMMIT;

