INSERT INTO `ubuzima`.`ubuzima_fieldcategory` (`id`, `name`) VALUES (NULL, 'ANC'), (NULL, 'PNC');

UPDATE `ubuzima`.`ubuzima_fieldtype` SET `category_id` = '7' WHERE `ubuzima_fieldtype`.`id` =55;

UPDATE `ubuzima`.`ubuzima_fieldtype` SET `category_id` = '7' WHERE `ubuzima_fieldtype`.`id` =56;

UPDATE `ubuzima`.`ubuzima_fieldtype` SET `category_id` = '7' WHERE `ubuzima_fieldtype`.`id` =57;

INSERT INTO `ubuzima`.`ubuzima_fieldtype` (
`id` ,
`key` ,
`description` ,
`category_id` ,
`has_value`
)
VALUES (
NULL , 'pnc1', 'First post natal care visit, this happens 2 days after delivery date', '8', '0'
);

INSERT INTO `ubuzima`.`ubuzima_fieldtype` (
`id` ,
`key` ,
`description` ,
`category_id` ,
`has_value`
)
VALUES (
NULL , 'pnc2', 'Second post natal care visit, this happens 6 days after delivery date', '8', '0'
);

INSERT INTO `ubuzima`.`ubuzima_fieldtype` (
`id` ,
`key` ,
`description` ,
`category_id` ,
`has_value`
)
VALUES (
NULL , 'pnc3', 'Third post natal care visit, this happens 28 days after delivery date', '8', '0'
);


ALTER TABLE `ubuzima_field` ADD `report_id` INT NULL AFTER `type_id`;
ALTER TABLE `ubuzima_field` ADD `village` VARCHAR( 255 ) NULL AFTER `report_id`;
ALTER TABLE `ubuzima_field` ADD `cell_id` INT NULL AFTER `village`;
ALTER TABLE `ubuzima_field` ADD `sector_id` INT NULL AFTER `cell_id`;
ALTER TABLE `ubuzima_field` ADD `district_id` INT NULL AFTER `sector_id`;
ALTER TABLE `ubuzima_field` ADD `province_id` INT NULL AFTER `district_id`;
ALTER TABLE `ubuzima_field` ADD `nation_id` INT NULL AFTER `province_id`;
ALTER TABLE `ubuzima_field` ADD	`creation` datetime NOT NULL AFTER `value`;

