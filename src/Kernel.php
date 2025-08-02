<?php

namespace App;

use Twig\Environment;
use Twig\Loader\FilesystemLoader;

class Kernel
{

    public function runController(): void
    {
        $controllerParam = $_GET['controller'] ?? 'app';
        $viewParam = $_GET['view'] ?? 'index';

        $controllerClass = 'App\\Controller\\' . ucfirst($controllerParam) . 'Controller';

        if (!class_exists($controllerClass)) {
            http_response_code(404);
            echo "Controller '$controllerClass' not found.";
            return;
        }

        $controller = new $controllerClass();

        if (!method_exists($controller, $viewParam)) {
            http_response_code(404);
            echo "Methode '$viewParam' im Controller '$controllerClass' nicht gefunden.";
            return;
        }

        try {
            $content = call_user_func([$controller, $viewParam]);
            echo $content;
        } catch (\Throwable $e) {
            http_response_code(500);
            echo "Fehler im Controller: " . $e->getMessage();
        }
    }

}