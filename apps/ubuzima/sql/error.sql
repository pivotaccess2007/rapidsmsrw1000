CREATE TABLE `ubuzima_errortype` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(255) NOT NULL,
    `description` longtext NOT NULL
)
;
ALTER TABLE `ubuzima_errornote` ADD `type_id` integer NOT NULL DEFAULT 1 AFTER `errmsg`;
ALTER TABLE `ubuzima_errornote` ADD `identity` varchar(13) AFTER `errby_id`;
ALTER TABLE `ubuzima_errornote` CHANGE `errby_id` `errby_id` INT( 11 ) NULL; 
ALTER TABLE `ubuzima_errornote` ADD CONSTRAINT `type_id_refs_id_73d15121` FOREIGN KEY (`type_id`) REFERENCES `ubuzima_errortype` (`id`);

ALTER TABLE `ubuzima_errornote` ADD `village` VARCHAR( 255 ) NULL AFTER `type_id`;
ALTER TABLE `ubuzima_errornote` ADD `cell_id` INT NULL AFTER `village`;
ALTER TABLE `ubuzima_errornote` ADD `sector_id` INT NULL AFTER `cell_id`;
ALTER TABLE `ubuzima_errornote` ADD `district_id` INT NULL AFTER `sector_id`;
ALTER TABLE `ubuzima_errornote` ADD `province_id` INT NULL AFTER `district_id`;
ALTER TABLE `ubuzima_errornote` ADD `nation_id` INT NULL AFTER `province_id`;
