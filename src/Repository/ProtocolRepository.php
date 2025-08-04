<?php

namespace App\Repository;

use App\AbstractRepository;

class ProtocolRepository extends AbstractRepository
{

    public function findByProfile(int $id = 0): array
    {
        $this->db->prepare("
                    select
                        p.id as id,
                        sp.id as profile_id,
                        s.name as name,
                        s.id as speaker_id,
                        p.title,
                        p.whisper_model,
                        p.whisper_duration,
                        p.llm_model,
                        p.llm_duration,
                        p.device,
                        p.gpu,
                        p.audio_length,
                        p.timestamp
                    from protokoll p
                    join speaker_protocol spp on p.id = spp.protocol_id
                    join speaker s on s.id = spp.speaker_id
                    join speaker_profiles sp on sp.speaker_id = s.id
                    where s.id = :id
                    group by p.id
                    order by p.timestamp desc
                    ")
            ->bindParams([":id" => $id])
            ->flush();

        return $this->db->fetchAll();
    }

    public function findAll(): array
    {
        $this->db->prepare("
                    select
                        sp.id as profile_id,
                        count(s.name) as names,
                        p.id as id,
                        p.title,
                        p.whisper_model,
                        p.whisper_duration,
                        p.llm_model,
                        p.llm_duration,
                        p.device,
                        p.gpu,
                        p.audio_length,
                        p.timestamp
                    from protokoll p
                    join speaker_protocol spp on p.id = spp.protocol_id
                    join speaker s on s.id = spp.speaker_id
                    join speaker_profiles sp on sp.speaker_id = s.id
                    group by p.id
                    order by p.timestamp desc
                    ")
            ->flush();

        return $this->db->fetchAll();
    }

    public function find(int $id = 0): array
    {
        $this->db
            ->prepare("
                    select
                        p.id,
                        p.title,
                        p.transcript,
                        p.file,
                        p.cluster_file,
                        p.summary,
                        p.think,
                        p.whisper_model,
                        p.whisper_duration,
                        p.llm_model,
                        p.llm_duration,
                        p.device,
                        p.gpu,
                        p.audio_length,
                        p.timestamp
                    from protokoll p
                    where p.id = :id
                    limit 1
                    ")
            ->bindParams([":id" => $id])
            ->flush();

        return $this->db->fetchOne();
    }

}