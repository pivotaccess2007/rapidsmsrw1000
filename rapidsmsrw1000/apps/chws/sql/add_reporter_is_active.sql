-- This needs to be applied after updating changes based on ticket
-- https://github.com/pivotaccess2007/rapidsmsrw1000/issues/21

ALTER TABLE `chws_reporter` ADD `is_active` BOOLEAN NOT NULL AFTER `deactivated`;
