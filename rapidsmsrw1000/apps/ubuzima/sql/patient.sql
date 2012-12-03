ALTER TABLE `ubuzima_patient` ADD `telephone` VARCHAR( 13 ) NULL AFTER `national_id`;
ALTER TABLE `ubuzima_patient` ADD `village` VARCHAR( 255 ) NULL AFTER `telephone`;
ALTER TABLE `ubuzima_patient` ADD `cell_id` INT NULL AFTER `village`;
ALTER TABLE `ubuzima_patient` ADD `sector_id` INT NULL AFTER `cell_id`;
ALTER TABLE `ubuzima_patient` ADD `district_id` INT NULL AFTER `sector_id`;
ALTER TABLE `ubuzima_patient` ADD `province_id` INT NULL AFTER `district_id`;
ALTER TABLE `ubuzima_patient` ADD `nation_id` INT NULL AFTER `province_id`;
