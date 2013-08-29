ALTER TABLE `chws_province` ADD `minaloc_approved` BOOLEAN NOT NULL AFTER `nation_id`;
ALTER TABLE `chws_district` ADD `minaloc_approved` BOOLEAN NOT NULL AFTER `province_id`;
ALTER TABLE `chws_sector` ADD `minaloc_approved` BOOLEAN NOT NULL AFTER `district_id`;
ALTER TABLE `chws_cell` ADD `minaloc_approved` BOOLEAN NOT NULL AFTER `sector_id`;
ALTER TABLE `chws_village` ADD `minaloc_approved` BOOLEAN NOT NULL AFTER `cell_id`;
