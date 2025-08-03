<?php

namespace App\Service;

class VectorService
{

    public static function length(array|string $vector): float
    {
        if(is_string($vector))
            $vector = json_decode($vector);

        $sum = 0.0;
        foreach ($vector as $value) {
            $sum += $value ** 2;
        }
        return sqrt($sum);
    }

}