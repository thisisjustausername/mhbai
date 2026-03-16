#!/bin/bash

psql -d mhbs -c 'SELECT COUNT(*) FROM unia.modules_ai_extracted;' --tuples-only
