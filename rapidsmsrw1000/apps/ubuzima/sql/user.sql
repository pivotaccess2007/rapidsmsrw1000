
ALTER TABLE `ubuzima_userlocation` ADD `village` VARCHAR( 255 ) NULL AFTER `location_id`;
ALTER TABLE `ubuzima_userlocation` ADD `cell_id` INT NULL AFTER `village`;
ALTER TABLE `ubuzima_userlocation` ADD `sector_id` INT NULL AFTER `cell_id`;
ALTER TABLE `ubuzima_userlocation` ADD `district_id` INT NULL AFTER `sector_id`;
ALTER TABLE `ubuzima_userlocation` ADD `province_id` INT NULL AFTER `district_id`;
ALTER TABLE `ubuzima_userlocation` ADD `nation_id` INT NULL AFTER `province_id`;
