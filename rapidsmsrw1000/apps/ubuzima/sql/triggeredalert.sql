ALTER TABLE `ubuzima_triggeredalert` DROP `action_id` ;
ALTER TABLE `ubuzima_triggeredalert` ADD `village` VARCHAR( 255 ) NULL AFTER `trigger_id`;
ALTER TABLE `ubuzima_triggeredalert` ADD `cell_id` INT NULL AFTER `village`;
ALTER TABLE `ubuzima_triggeredalert` ADD `sector_id` INT NULL AFTER `cell_id`;
ALTER TABLE `ubuzima_triggeredalert` ADD `district_id` INT NULL AFTER `sector_id`;
ALTER TABLE `ubuzima_triggeredalert` ADD `province_id` INT NULL AFTER `district_id`;
ALTER TABLE `ubuzima_triggeredalert` ADD `nation_id` INT NULL AFTER `province_id`;

ALTER TABLE `ubuzima_triggeredalert` ADD `response` VARCHAR( 3 ) NULL DEFAULT 'NR' AFTER `date`;


