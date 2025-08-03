<?php

namespace App\Repository;

use App\AbstractRepository;

class SpeakerRepository extends AbstractRepository
{

    public function findSpeakersCountProfiles(?string $name): array
    {
        if ($name != null) {
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
                    where speaker.name LIKE :name
                    group by speaker.name
                    order by speaker.name
                    ")
                ->bindParams([":name" => "%{$name}%"]);
        } else {
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
                    ");
        }
        $this->db->flush();

        return $this->db->fetchAll();
    }

    public function findSpeakersCountProtocols(?string $name): array
    {
        if ($name != null) {
            $this->db->prepare("
                    select
                    speaker.id as speaker_id,
                    speaker_profiles.id,
                    speaker.name,
                    speaker.condition,
                    speaker.location,
                    speaker.microphone,
                    count(DISTINCT speaker_protocol.protocol_id) as protocols,
                    speaker_profiles.updated_at as updated,
                    speaker_profiles.id as profile_id
                    from speaker
                        left join speaker_protocol on speaker.id = speaker_protocol.speaker_id
                        left join speaker_profiles on speaker_profiles.speaker_id = speaker.id
                    where lower(speaker.name) = lower(:name)
                    group by speaker.id
                    order by speaker_profiles.updated_at desc
                    ")
                ->bindParams([":name" => "$name"]);

        } else {
            $this->db->prepare("
                    select
                    speaker.id as speaker_id,
                    speaker_profiles.id,
                    speaker.name,
                    speaker.condition,
                    speaker.location,
                    speaker.microphone,
                    count(DISTINCT speaker_protocol.protocol_id) as protocols,
                    speaker_profiles.updated_at as updated,
                    speaker_profiles.id as profile_id
                    from speaker
                        left join speaker_protocol on speaker.id = speaker_protocol.speaker_id
                        left join speaker_profiles on speaker_profiles.speaker_id = speaker.id
                    group by speaker.id
                    order by speaker.name, speaker_profiles.updated_at desc
                    ");
        }

        $this->db->flush();

        return $this->db->fetchAll();
    }

}