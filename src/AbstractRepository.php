<?php

namespace App;

use App\Model\SQLite;

abstract class AbstractRepository
{
    protected SQLite $db;

    public function __construct()
    {
        $this->db = new SQLite();
    }

}