ALTER TABLE `reporters_reporter` ADD `telephone` VARCHAR( 13 ) NULL AFTER `role_id`;
ALTER TABLE `reporters_reporter` ADD `cell_id` INT NULL AFTER `village`;
ALTER TABLE `reporters_reporter` ADD `sector_id` INT NULL AFTER `cell_id`;
ALTER TABLE `reporters_reporter` ADD `district_id` INT NULL AFTER `sector_id`;
ALTER TABLE `reporters_reporter` ADD `province_id` INT NULL AFTER `district_id`;
ALTER TABLE `reporters_reporter` ADD `nation_id` INT NULL AFTER `province_id`;

