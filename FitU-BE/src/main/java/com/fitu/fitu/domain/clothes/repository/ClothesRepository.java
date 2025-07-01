package com.fitu.fitu.domain.clothes.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import com.fitu.fitu.domain.clothes.entity.Clothes;

@Repository
public interface ClothesRepository extends JpaRepository<Clothes, Long>, ClothesCustomRepository {
  @Query("SELECT c FROM Clothes c WHERE c.userId = :userId ORDER BY c.createdAt DESC")
  List<Clothes> findByUserId(@Param("userId") String userId);
}
