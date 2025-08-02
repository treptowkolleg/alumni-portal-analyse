<?php

namespace App\Repository;

use App\AbstractRepository;

class SpeakerRepository extends AbstractRepository
{

    public function findSpeakersCountProfiles(): array
    {
        $this->db->prepare("
                    select
                    speaker.id,
                    speaker.name,
                    speaker.condition,
                    speaker.location,
                    speaker.microphone,
                    count(speaker_profiles.id) as profiles,
                    speaker_profiles.updated_at as updated
                    from speaker
                        left join speaker_profiles on speaker_profiles.speaker_id = speaker.id
                    group by speaker.name
                    order by speaker.name
                    ")
            ->flush();

        return $this->db->fetchAll();
    }

    public function findSpeakersCountProtocols(?string $name): array
    {
        if ($name !== null) {
            $this->db->prepare("
                    select
                    speaker.id,
                    speaker.name,
                    speaker.condition,
                    speaker.location,
                    speaker.microphone,
                    count(speaker_protocol.protocol_id) as protocols,
                    speaker_profiles.updated_at as updated
                    from speaker
                        left join speaker_protocol on speaker.id = speaker_protocol.speaker_id
                        left join speaker_profiles on speaker_profiles.speaker_id = speaker.id
                    where lower(speaker.name) = lower(:name)
                    group by speaker.id
                    order by speaker.name
                    ")
                ->bindParams([":name" => $name]);

        } else {
            $this->db->prepare("
                    select
                    speaker.id,
                    speaker.name,
                    speaker.condition,
                    speaker.location,
                    speaker.microphone,
                    count(speaker_protocol.protocol_id) as protocols,
                    speaker_profiles.updated_at as updated
                    from speaker
                        left join speaker_protocol on speaker.id = speaker_protocol.speaker_id
                        left join speaker_profiles on speaker_profiles.speaker_id = speaker.id
                    group by speaker.id
                    order by speaker.name
                    ");
        }

        $this->db->flush();

        return $this->db->fetchAll();
    }

}