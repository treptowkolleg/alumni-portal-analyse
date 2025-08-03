<?php

namespace App\Controller;

use App\AbstractController;
use App\Repository\EmbeddingRepository;
use App\Repository\SpeakerRepository;
use App\Service\VectorService;
use Twig\Error\LoaderError;
use Twig\Error\RuntimeError;
use Twig\Error\SyntaxError;

class EmbeddingController extends AbstractController
{

    /**
     * @throws SyntaxError
     * @throws RuntimeError
     * @throws LoaderError
     */
    public function index(): string
    {
        $repository = new EmbeddingRepository();
        $embeddings = $repository->findByProfile($_GET['profile_id'] ?? 0);

        foreach ($embeddings as &$row) {
            if (isset($row['embedding']) && is_string($row['embedding'])) {
                // Beträge der Vektoren berechnen und an original Position speichern.
                $row['embedding_length'] = VectorService::length($row['embedding']);
                $curr = $row['embedding_length'];
                $avg = VectorService::length($row['avg']);
                $row['embedding_avg'] = $avg;
                $row['angle'] = -$avg + $curr;
            }
        }
        unset($row);

        return $this->render('app/embedding/index.html.twig', [
            'embeddings' => $embeddings,
        ]);
    }

}