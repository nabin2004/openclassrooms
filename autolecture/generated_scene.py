from manim import *

class QKVDotProduct(ZoomedScene):
    def construct(self):
        # --- Object Initialization ---
        # Hero word 'it' and its embedding
        self.it_embedding_rect = Rectangle(width=1.5, height=0.5, color=BLUE, fill_opacity=0.8)
        self.it_text = Text("'it'", font_size=36, color=WHITE).move_to(self.it_embedding_rect)
        self.it_group = VGroup(self.it_embedding_rect, self.it_text).center().shift(UP * 1.5)

        # Supporting words 'animal' and 'street' with their embeddings
        self.animal_embedding_rect = Rectangle(width=1.2, height=0.4, color=BLUE, fill_opacity=0.8)
        self.animal_text = Text("'animal'", font_size=28, color=WHITE).move_to(self.animal_embedding_rect)
        self.animal_group = VGroup(self.animal_embedding_rect, self.animal_text).next_to(self.it_group, LEFT * 3 + DOWN, buff=1.0)

        self.street_embedding_rect = Rectangle(width=1.2, height=0.4, color=BLUE, fill_opacity=0.8)
        self.street_text = Text("'street'", font_size=28, color=WHITE).move_to(self.street_embedding_rect)
        self.street_group = VGroup(self.street_embedding_rect, self.street_text).next_to(self.it_group, RIGHT * 3 + DOWN, buff=1.0)

        # Query, Key, Value vectors for 'it'
        self.it_query_rect = Rectangle(width=1.0, height=0.4, color=GOLD, fill_opacity=0.8)
        self.it_query_label = Text("Q", font_size=24, color=BLACK).move_to(self.it_query_rect)
        self.it_query_group = VGroup(self.it_query_rect, self.it_query_label).next_to(self.it_embedding_rect, RIGHT, buff=0.7)

        self.it_key_rect = Rectangle(width=1.0, height=0.4, color=GOLD, fill_opacity=0.8)
        self.it_key_label = Text("K", font_size=24, color=BLACK).move_to(self.it_key_rect)
        self.it_key_group = VGroup(self.it_key_rect, self.it_key_label).next_to(self.it_embedding_rect, LEFT, buff=0.7)

        self.it_value_rect = Rectangle(width=1.0, height=0.4, color=BLUE, fill_opacity=0.8)
        self.it_value_label = Text("V", font_size=24, color=WHITE).move_to(self.it_value_rect)
        self.it_value_group = VGroup(self.it_value_rect, self.it_value_label).next_to(self.it_embedding_rect, UP, buff=0.7)

        # Key, Value vectors for 'animal'
        self.animal_key_rect = Rectangle(width=0.8, height=0.3, color=GOLD, fill_opacity=0.3)  # Start dimmed
        self.animal_key_label = Text("K", font_size=20, color=BLACK).move_to(self.animal_key_rect)
        self.animal_key_group = VGroup(self.animal_key_rect, self.animal_key_label).next_to(self.animal_embedding_rect, DOWN, buff=0.5)

        self.animal_value_rect = Rectangle(width=0.8, height=0.3, color=BLUE, fill_opacity=0.8)
        self.animal_value_label = Text("V", font_size=20, color=WHITE).move_to(self.animal_value_rect)
        self.animal_value_group = VGroup(self.animal_value_rect, self.animal_value_label).next_to(self.animal_key_group, DOWN, buff=0.3)

        # Key, Value vectors for 'street'
        self.street_key_rect = Rectangle(width=0.8, height=0.3, color=GOLD, fill_opacity=0.3)  # Start dimmed
        self.street_key_label = Text("K", font_size=20, color=BLACK).move_to(self.street_key_rect)
        self.street_key_group = VGroup(self.street_key_rect, self.street_key_label).next_to(self.street_embedding_rect, DOWN, buff=0.5)

        self.street_value_rect = Rectangle(width=0.8, height=0.3, color=BLUE, fill_opacity=0.8)
        self.street_value_label = Text("V", font_size=20, color=WHITE).move_to(self.street_value_rect)
        self.street_value_group = VGroup(self.street_value_rect, self.street_value_label).next_to(self.street_key_group, DOWN, buff=0.3)

        # Comparison elements (arrows, dot products, scores)
        self.query_to_animal_key_arrow = Arrow(ORIGIN, ORIGIN, buff=0.1, stroke_width=6, color=GOLD).set_opacity(0)
        self.dot_product_symbol_animal_text = Text("•", font_size=40, color=GOLD)
        self.score_it_animal_text = Text("0.9", font_size=36, color=GREEN)

        self.query_to_street_key_arrow = Arrow(ORIGIN, ORIGIN, buff=0.1, stroke_width=6, color=GOLD).set_opacity(0)
        self.dot_product_symbol_street_text = Text("•", font_size=40, color=GOLD)
        self.score_it_street_text = Text("0.1", font_size=36, color=RED)

        # Weighted sum elements
        self.mult_symbol_animal = Text("x", font_size=36, color=GOLD).scale(0.8)
        self.mult_symbol_street = Text("x", font_size=36, color=GOLD).scale(0.8)
        self.summation_symbol = Text("+", font_size=48, color=GOLD)

        self.final_it_representation = Rectangle(width=2.5, height=0.7, color=GREEN, fill_opacity=0.9)
        self.final_it_label = Text("New 'it' (context-aware)", font_size=28, color=BLACK).move_to(self.final_it_representation)

        # --- Animations ---
        # 1. Introduce initial words and embeddings
        self.play(FadeIn(self.it_group, run_time=0.5))
        self.wait(0.2)
        self.play(FadeIn(self.animal_group, run_time=0.5), FadeIn(self.street_group, run_time=0.5))
        self.wait(0.8)

        # 2. Zoom in and reveal Q, K, V for 'it'
        self.play(
            self.camera.frame.animate.scale(0.8).move_to(self.it_group.get_center() + DOWN * 0.5),
            run_time=1.0
        )
        self.wait(0.2)
        self.play(FadeIn(self.it_query_group, run_time=1.0))
        self.wait(0.2)
        self.play(FadeIn(self.it_key_group, run_time=1.0), FadeIn(self.it_value_group, run_time=1.0))
        self.wait(0.8)

        # 3. Reveal K, V for 'animal' and 'street'
        self.play(
            FadeIn(self.animal_key_group, run_time=0.5),
            FadeIn(self.animal_value_group, run_time=0.5),
            FadeIn(self.street_key_group, run_time=0.5),
            FadeIn(self.street_value_group, run_time=0.5)
        )
        self.wait(0.8)

        # 4. Compare 'it' Query with 'animal' Key (Dot Product)
        self.query_to_animal_key_arrow.put_start_and_end_on(self.it_query_rect.get_left(), self.animal_key_rect.get_right())
        self.dot_product_symbol_animal_text.move_to(self.query_to_animal_key_arrow.get_center())
        self.play(
            GrowArrow(self.query_to_animal_key_arrow, run_time=1.0),
            FadeIn(self.dot_product_symbol_animal_text, run_time=0.5)
        )
        self.wait(0.2)
        self.play(self.animal_key_group.animate.set_fill(GOLD, opacity=0.8), run_time=0.5)
        self.wait(0.8)
        self.score_it_animal_text.move_to(self.dot_product_symbol_animal_text.get_center())
        self.play(ReplacementTransform(self.dot_product_symbol_animal_text, self.score_it_animal_text, run_time=1.0))
        self.wait(0.8)

        # 5. Compare 'it' Query with 'street' Key (Dot Product)
        self.play(
            self.animal_key_group.animate.set_fill(GOLD, opacity=0.3),
            FadeOut(self.query_to_animal_key_arrow, run_time=0.5)
        )
        self.wait(0.2)
        self.query_to_street_key_arrow.put_start_and_end_on(self.it_query_rect.get_left(), self.street_key_rect.get_right())
        self.dot_product_symbol_street_text.move_to(self.query_to_street_key_arrow.get_center())
        self.play(
            GrowArrow(self.query_to_street_key_arrow, run_time=1.0),
            FadeIn(self.dot_product_symbol_street_text, run_time=0.5)
        )
        self.wait(0.2)
        self.play(self.street_key_group.animate.set_fill(GOLD, opacity=0.8), run_time=0.5)
        self.wait(0.8)
        self.score_it_street_text.move_to(self.dot_product_symbol_street_text.get_center())
        self.play(ReplacementTransform(self.dot_product_symbol_street_text, self.score_it_street_text, run_time=1.0))
        self.wait(0.8)

        # 6. Weighted sum of Values
        self.play(
            self.street_key_group.animate.set_fill(GOLD, opacity=0.3),
            FadeOut(self.query_to_street_key_arrow, run_time=0.5)
        )
        self.wait(0.2)

        animal_score_target_pos = self.animal_value_group.get_left() + LEFT * 0.7
        street_score_target_pos = self.street_value_group.get_left() + LEFT * 0.7
        self.mult_symbol_animal.next_to(animal_score_target_pos, RIGHT, buff=0.1)
        self.mult_symbol_street.next_to(street_score_target_pos, RIGHT, buff=0.1)

        self.play(
            self.score_it_animal_text.animate.move_to(animal_score_target_pos),
            FadeIn(self.mult_symbol_animal, run_time=0.5),
            self.score_it_street_text.animate.move_to(street_score_target_pos),
            FadeIn(self.mult_symbol_street, run_time=0.5),
            run_time=1.0
        )
        self.wait(0.2)
        self.play(
            self.animal_value_group.animate.set_fill(GOLD, opacity=0.8),
            self.street_value_group.animate.set_fill(GOLD, opacity=0.8),
            run_time=0.5
        )
        self.wait(0.8)

        animal_weighted_group = VGroup(self.score_it_animal_text, self.mult_symbol_animal, self.animal_value_group)
        street_weighted_group = VGroup(self.score_it_street_text, self.mult_symbol_street, self.street_value_group)

        sum_pos_animal = self.it_group.get_center() + DOWN*2 + LEFT*1.2
        sum_pos_street = self.it_group.get_center() + DOWN*2 + RIGHT*1.2
        sum_symbol_pos = self.it_group.get_center() + DOWN*2

        self.play(
            animal_weighted_group.animate.move_to(sum_pos_animal),
            street_weighted_group.animate.move_to(sum_pos_street),
            FadeIn(self.summation_symbol.move_to(sum_symbol_pos), run_time=0.5),
            run_time=1.5
        )
        self.wait(0.2)

        self.final_it_representation.next_to(self.summation_symbol, DOWN, buff=0.8)
        self.final_it_label.move_to(self.final_it_representation.get_center())

        self.play(
            Create(self.final_it_representation, run_time=1.0),
            FadeIn(self.final_it_label, run_time=0.5),
            FadeOut(animal_weighted_group, shift=UP*0.5, run_time=0.5),
            FadeOut(street_weighted_group, shift=UP*0.5, run_time=0.5),
            FadeOut(self.summation_symbol, shift=UP*0.5, run_time=0.5)
        )
        self.wait(0.8)