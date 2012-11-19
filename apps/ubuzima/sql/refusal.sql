ALTER TABLE `ubuzima_refusal` ADD `village` VARCHAR( 255 ) NULL AFTER `refid`;
ALTER TABLE `ubuzima_refusal` ADD `cell_id` INT NULL AFTER `village`;
ALTER TABLE `ubuzima_refusal` ADD `sector_id` INT NULL AFTER `cell_id`;
ALTER TABLE `ubuzima_refusal` ADD `district_id` INT NULL AFTER `sector_id`;
ALTER TABLE `ubuzima_refusal` ADD `province_id` INT NULL AFTER `district_id`;
ALTER TABLE `ubuzima_refusal` ADD `nation_id` INT NULL AFTER `province_id`;
