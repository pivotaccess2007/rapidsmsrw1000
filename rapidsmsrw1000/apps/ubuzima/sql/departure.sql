ALTER TABLE `ubuzima_departure` ADD `dob` DATE NULL AFTER `depid`;
ALTER TABLE `ubuzima_departure` ADD `child_number` INT NULL AFTER `dob`;
ALTER TABLE `ubuzima_departure` ADD `village` VARCHAR( 255 ) NULL AFTER `child_number`;
ALTER TABLE `ubuzima_departure` ADD `cell_id` INT NULL AFTER `village`;
ALTER TABLE `ubuzima_departure` ADD `sector_id` INT NULL AFTER `cell_id`;
ALTER TABLE `ubuzima_departure` ADD `district_id` INT NULL AFTER `sector_id`;
ALTER TABLE `ubuzima_departure` ADD `province_id` INT NULL AFTER `district_id`;
ALTER TABLE `ubuzima_departure` ADD `nation_id` INT NULL AFTER `province_id`;

