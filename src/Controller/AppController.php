<?php

namespace App\Controller;

use App\AbstractController;
use App\Repository\SpeakerRepository;
use Twig\Error\LoaderError;
use Twig\Error\RuntimeError;
use Twig\Error\SyntaxError;

class AppController extends AbstractController
{

    /**
     * @throws SyntaxError
     * @throws RuntimeError
     * @throws LoaderError
     */
    public function index(): string
    {
        $filteredName = $_GET['name'] ?? '';
        $repository = new SpeakerRepository();
        $speakers = $repository->findSpeakersCountProfiles($filteredName);

        return $this->render('app/speaker/index.html.twig', [
            'speakers' => $speakers,
            'filtered_name' => $filteredName,
        ]);
    }

    /**
     * @throws SyntaxError
     * @throws RuntimeError
     * @throws LoaderError
     */
    public function show_profiles(): string
    {
        $filteredName = $_GET['name'] ?? '';
        $repository = new SpeakerRepository();
        $speakers = $repository->findSpeakersCountProtocols($filteredName);

        return $this->render('app/speaker/show_profiles.html.twig', [
            'speakers' => $speakers,
            'filtered_name' => $filteredName,
        ]);
    }


}