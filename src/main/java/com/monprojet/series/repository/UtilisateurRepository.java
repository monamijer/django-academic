package com.monprojet.series.repository;

import com.monprojet.series.entity.StatutUtilisateur;
import com.monprojet.series.entity.Utilisateur;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface UtilisateurRepository extends JpaRepository<Utilisateur, Long> {

    Optional<Utilisateur> findByEmail(String email);

    Optional<Utilisateur> findByPseudo(String pseudo);

    boolean existsByEmail(String email);

    List<Utilisateur> findByStatutOrderByDateInscriptionAsc(StatutUtilisateur statut);

    long countByStatut(StatutUtilisateur statut);
}