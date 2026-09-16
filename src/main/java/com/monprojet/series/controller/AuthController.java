// AuthController.java
package com.monprojet.series.controller;

import com.monprojet.series.dto.request.ConnexionRequest;
import com.monprojet.series.dto.request.InscriptionRequest;
import com.monprojet.series.dto.response.AuthResponse;
import com.monprojet.series.entity.StatutUtilisateur;
import com.monprojet.series.entity.Utilisateur;
import com.monprojet.series.exception.BusinessException;
import com.monprojet.series.repository.UtilisateurRepository;
import com.monprojet.series.security.JwtService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final UtilisateurRepository utilisateurRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuthenticationManager authenticationManager;
    private final JwtService jwtService;

    @PostMapping("/inscription")
    public ResponseEntity<AuthResponse> inscription(@Valid @RequestBody InscriptionRequest request) {
        if (utilisateurRepository.existsByEmail(request.email())) {
            throw new BusinessException("Cet email est déjà utilisé.");
        }

        Utilisateur utilisateur = Utilisateur.builder()
                .pseudo(request.pseudo())
                .email(request.email())
                .motDePasse(passwordEncoder.encode(request.motDePasse()))
                // statut = EN_ATTENTE par défaut (voir l'entité)
                .build();

        utilisateur = utilisateurRepository.save(utilisateur);

        // Pas de token tant que le compte n'est pas approuvé.
        // Le front affichera un message d'attente.
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(new AuthResponse(
                        null, // pas de token
                        utilisateur.getId(),
                        utilisateur.getPseudo(),
                        utilisateur.getRole().name(),
                        utilisateur.getStatut().name(),
                        "Votre compte a été créé et est en attente d'approbation par un administrateur."
                ));
    }

    @PostMapping("/connexion")
    public AuthResponse connexion(@Valid @RequestBody ConnexionRequest request) {
        // 1. Authentification classique (email + mot de passe)
        try {
            authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(request.email(), request.motDePasse())
            );
        } catch (BadCredentialsException e) {
            throw new BusinessException("Email ou mot de passe incorrect.");
        }

        Utilisateur utilisateur = utilisateurRepository.findByEmail(request.email())
                .orElseThrow(() -> new BusinessException("Email ou mot de passe incorrect."));

        // 2. Vérification du statut AVANT de générer le token
        if (utilisateur.getStatut() == StatutUtilisateur.EN_ATTENTE) {
            throw new BusinessException(
                    "Votre compte est en attente d'approbation par un administrateur."
            );
        }
        if (utilisateur.getStatut() == StatutUtilisateur.REFUSE) {
            throw new BusinessException(
                    "Votre compte a été refusé. Contactez un administrateur."
            );
        }

        // 3. Mise à jour de la dernière connexion
        utilisateur.setDerniereConnexion(LocalDateTime.now());
        utilisateurRepository.save(utilisateur);

        // 4. Génération du token
        String token = jwtService.genererToken(
                (UserDetails) org.springframework.security.core.userdetails.User
                        .withUsername(utilisateur.getEmail())
                        .password(utilisateur.getMotDePasse())
                        .authorities("ROLE_" + utilisateur.getRole().name())
                        .build()
        );

        return new AuthResponse(
                token,
                utilisateur.getId(),
                utilisateur.getPseudo(),
                utilisateur.getRole().name(),
                utilisateur.getStatut().name(),
                "Connexion réussie."
        );
    }
}