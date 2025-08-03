<?php

namespace App\Controller;

use App\AbstractController;
use App\Repository\ProtocolRepository;
use cebe\markdown\GithubMarkdown;
use cebe\markdown\MarkdownExtra;
use Twig\Error\LoaderError;
use Twig\Error\RuntimeError;
use Twig\Error\SyntaxError;

class ProtocolController extends AbstractController
{

    /**
     * @throws SyntaxError
     * @throws RuntimeError
     * @throws LoaderError
     */
    public function index(): string
    {
        $repository = new ProtocolRepository();

        $profileId = $_GET['user_id'] ?? 0;

        if($profileId){
            $protocols = $repository->findByProfile($profileId);
            $tableTemplate = 'tables/protocol_table.html.twig';
        } else {
            $protocols = $repository->findAll();
            $tableTemplate = 'tables/protocol_multiuser_table.html.twig';
        }


        return $this->render('app/protocol/index.html.twig', [
            'protocols' => $protocols,
            'table_template' => $tableTemplate,
        ]);
    }

    /**
     * @throws SyntaxError
     * @throws RuntimeError
     * @throws LoaderError
     */
    public function show(): string
    {
        $repository = new ProtocolRepository();
        $parser = new GithubMarkdown();

        $protocol = $repository->find($_GET['protocol_id'] ?? 0);

        $protocol['summary'] = $parser->parse($protocol['summary']);

        return $this->render('app/protocol/show.html.twig', [
            'protocol' => $protocol,
        ]);
    }

}