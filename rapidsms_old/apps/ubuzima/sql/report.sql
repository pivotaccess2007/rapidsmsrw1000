INSERT INTO `ubuzima`.`ubuzima_reporttype` (
`id` ,
`name`
)
VALUES (
NULL , 'PNC'
);

ALTER TABLE `ubuzima_report` ADD `edd_date` date NULL AFTER `date`;
ALTER TABLE `ubuzima_report` ADD `bmi_anc1` decimal(10,5) NULL AFTER `edd_date`;
ALTER TABLE `ubuzima_report` ADD `edd_anc2_date` date NULL AFTER `bmi_anc1`;
ALTER TABLE `ubuzima_report` ADD `edd_anc3_date` date NULL AFTER `edd_anc2_date`;
ALTER TABLE `ubuzima_report` ADD `edd_anc4_date` date NULL AFTER `edd_anc3_date`;
ALTER TABLE `ubuzima_report` ADD `edd_pnc1_date` date NULL AFTER `edd_anc4_date`;
ALTER TABLE `ubuzima_report` ADD `edd_pnc2_date` date NULL AFTER `edd_pnc1_date`;
ALTER TABLE `ubuzima_report` ADD `edd_pnc3_date` date NULL AFTER `edd_pnc2_date`;
ALTER TABLE `ubuzima_report` ADD `cell_id` INT NULL AFTER `village`;
ALTER TABLE `ubuzima_report` ADD `sector_id` INT NULL AFTER `cell_id`;
ALTER TABLE `ubuzima_report` ADD `district_id` INT NULL AFTER `sector_id`;
ALTER TABLE `ubuzima_report` ADD `province_id` INT NULL AFTER `district_id`;
ALTER TABLE `ubuzima_report` ADD `nation_id` INT NULL AFTER `province_id`;

