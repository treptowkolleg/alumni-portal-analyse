<?php

use App\Kernel;

require_once 'vendor/autoload.php';

const root = __DIR__;
const debug = true;

$app = new Kernel();
$app->runController();