ALTER TABLE `ubuzima_reminder` ADD `village` VARCHAR( 255 ) NULL AFTER `type_id`;
ALTER TABLE `ubuzima_reminder` ADD `cell_id` INT NULL AFTER `village`;
ALTER TABLE `ubuzima_reminder` ADD `sector_id` INT NULL AFTER `cell_id`;
ALTER TABLE `ubuzima_reminder` ADD `district_id` INT NULL AFTER `sector_id`;
ALTER TABLE `ubuzima_reminder` ADD `province_id` INT NULL AFTER `district_id`;
ALTER TABLE `ubuzima_reminder` ADD `nation_id` INT NULL AFTER `province_id`;
