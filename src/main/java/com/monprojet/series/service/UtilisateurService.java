// UtilisateurService.java
package com.monprojet.series.service;

import com.monprojet.series.dto.response.StatistiquesAdminResponse;
import com.monprojet.series.entity.RoleUtilisateur;
import com.monprojet.series.entity.StatutUtilisateur;
import com.monprojet.series.entity.Utilisateur;
import com.monprojet.series.exception.BusinessException;
import com.monprojet.series.exception.ResourceNotFoundException;
import com.monprojet.series.repository.UtilisateurRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional
public class UtilisateurService {

    private final UtilisateurRepository utilisateurRepository;
    private final PasswordEncoder passwordEncoder;

    @Transactional(readOnly = true)
    public List<Utilisateur> listerTous() {
        return utilisateurRepository.findAll();
    }

    @Transactional(readOnly = true)
    public List<Utilisateur> listerParStatut(StatutUtilisateur statut) {
        return utilisateurRepository.findByStatutOrderByDateInscriptionAsc(statut);
    }

    @Transactional(readOnly = true)
    public Utilisateur obtenirParId(Long id) {
        return utilisateurRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Utilisateur introuvable : id=" + id));
    }

    public Utilisateur creer(Utilisateur utilisateur) {
        if (utilisateurRepository.existsByEmail(utilisateur.getEmail())) {
            throw new BusinessException("Cet email est déjà utilisé : " + utilisateur.getEmail());
        }
        return utilisateurRepository.save(utilisateur);
    }

    @Transactional(readOnly = true)
    public Utilisateur obtenirParEmail(String email) {
        return utilisateurRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("Utilisateur introuvable : email=" + email));
    }

    // ---------- Actions admin ----------

    public Utilisateur approuver(Long id) {
        Utilisateur u = obtenirParId(id);
        u.setStatut(StatutUtilisateur.APPROUVE);
        return utilisateurRepository.save(u);
    }

    public Utilisateur refuser(Long id) {
        Utilisateur u = obtenirParId(id);
        u.setStatut(StatutUtilisateur.REFUSE);
        return utilisateurRepository.save(u);
    }

    public Utilisateur promouvoir(Long id) {
        Utilisateur u = obtenirParId(id);
        u.setRole(RoleUtilisateur.ADMIN);
        return utilisateurRepository.save(u);
    }

    public Utilisateur retrograder(Long id) {
        Utilisateur u = obtenirParId(id);
        u.setRole(RoleUtilisateur.USER);
        return utilisateurRepository.save(u);
    }

    public Utilisateur changerMotDePasse(Long id, String nouveauMotDePasse) {
        Utilisateur u = obtenirParId(id);
        u.setMotDePasse(passwordEncoder.encode(nouveauMotDePasse));
        return utilisateurRepository.save(u);
    }

    /**
     * Suppression en cascade : JPA s'occupe de supprimer les Visionnage et Serie
     * associés grâce à cascade = CascadeType.ALL sur les relations.
     */
    public void supprimer(Long id) {
        Utilisateur u = obtenirParId(id);
        utilisateurRepository.delete(u);
    }

    @Transactional(readOnly = true)
    public StatistiquesAdminResponse statistiques() {
        long total = utilisateurRepository.count();
        long attente = utilisateurRepository.countByStatut(StatutUtilisateur.EN_ATTENTE);
        long approuves = utilisateurRepository.countByStatut(StatutUtilisateur.APPROUVE);
        long refuses = utilisateurRepository.countByStatut(StatutUtilisateur.REFUSE);
        long admins = utilisateurRepository.findAll().stream()
                .filter(u -> u.getRole() == RoleUtilisateur.ADMIN)
                .count();
        return new StatistiquesAdminResponse(total, attente, approuves, refuses, admins);
    }
}