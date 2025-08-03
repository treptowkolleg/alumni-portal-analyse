<?php

namespace App\Repository;

use App\AbstractRepository;

class EmbeddingRepository extends AbstractRepository
{

    public function findByProfile(int $id = 0): array
    {
        $this->db->prepare("
                    select
                        e.id as id,
                        sp.embedding_avg as avg,
                        e.speaker_id as profile_id,
                        e.embedding as embedding,
                        e.created_at as created,
                        s.name as name
                    from speaker_embeddings e
                    join speaker_profiles sp on e.speaker_id = sp.id
                    join speaker s on sp.speaker_id = s.id
                    where e.speaker_id = :id
                    ")
            ->bindParams([":id" => $id])
            ->flush();

        return $this->db->fetchAll();
    }

}