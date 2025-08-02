<?php

namespace App\Controller;

use App\AbstractController;
use App\Model\SQLite;
use PDOException;
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
        $db = new SQLite();

        try {
            $db->prepare("
                        select speaker.id, speaker.name, speaker.condition, speaker.location, speaker.microphone, count(speaker_protocol.protocol_id) as protocols, speaker_profiles.updated_at as updated
                        from speaker
                            left join speaker_protocol on speaker.id = speaker_protocol.speaker_id
                            left join speaker_profiles on speaker_profiles.speaker_id = speaker.id
                        group by speaker.id
                        order by speaker.name
                    ")
                ->flush();

            $speakers = $db->fetchAll();
        } catch (PDOException $e) {
            $speakers = [];
        }

        return $this->render('app/index.html.twig', [
            'speakers' => $speakers,
        ]);
    }

}